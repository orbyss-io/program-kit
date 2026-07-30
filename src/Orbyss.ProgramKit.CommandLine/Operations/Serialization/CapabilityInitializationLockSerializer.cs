using System.Text.Json;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Serialization;

/// <summary>Strict source-generated capability ownership lock serializer.</summary>
public sealed class CapabilityInitializationLockSerializer :
    ICapabilityInitializationLockSerializer
{
    /// <inheritdoc />
    public CapabilityInitializationLock Read(ReadOnlySpan<byte> content)
    {
        var lockVersion = ReadLockVersion(content);
        return lockVersion switch
        {
            "1.0.0" => ReadLegacy(content),
            "2.0.0" => ReadCurrent(content),
            _ => throw new JsonException(
                "The capability ownership lock version is unsupported."),
        };
    }

    /// <inheritdoc />
    public byte[] Write(CapabilityInitializationLock value) =>
        JsonSerializer.SerializeToUtf8Bytes(
            value,
            CapabilityInitializationJsonContext.Default
                .CapabilityInitializationLock);

    private static CapabilityInitializationLock ReadCurrent(
        ReadOnlySpan<byte> content) =>
        JsonSerializer.Deserialize(
            content,
            CapabilityInitializationJsonContext.Default
                .CapabilityInitializationLock)
        ?? throw new JsonException(
            "The capability ownership lock cannot be JSON null.");

    private static CapabilityInitializationLock ReadLegacy(
        ReadOnlySpan<byte> content)
    {
        var legacy = JsonSerializer.Deserialize(
            content,
            CapabilityInitializationJsonContext.Default
                .LegacyCapabilityInitializationLock)
            ?? throw new JsonException(
                "The legacy capability ownership lock cannot be JSON null.");
        return new CapabilityInitializationLock(
            legacy.LockVersion,
            [
                new CapabilityProviderInitializationLock(
                    legacy.Provider,
                    legacy.BundleVersion,
                    legacy.ProgramKitRoot,
                    legacy.ManifestSha256,
                    legacy.Capabilities),
            ]);
    }

    private static string ReadLockVersion(ReadOnlySpan<byte> content)
    {
        Utf8JsonReader reader = new(
            content,
            new JsonReaderOptions
            {
                AllowTrailingCommas = false,
                CommentHandling = JsonCommentHandling.Disallow,
                MaxDepth = 64,
            });
        if (!reader.Read() || reader.TokenType != JsonTokenType.StartObject)
        {
            throw new JsonException(
                "The capability ownership lock must be one JSON object.");
        }

        string? lockVersion = null;
        var propertyNames = new HashSet<string>(StringComparer.Ordinal);
        var completed = false;
        while (reader.Read())
        {
            if (reader.TokenType == JsonTokenType.EndObject)
            {
                completed = true;
                break;
            }

            if (reader.TokenType != JsonTokenType.PropertyName)
            {
                throw new JsonException(
                    "The capability ownership lock has an invalid property.");
            }

            var propertyName = reader.GetString() ??
                throw new JsonException(
                    "The capability ownership lock has a null property name.");
            if (!propertyNames.Add(propertyName) || !reader.Read())
            {
                throw new JsonException(
                    "The capability ownership lock has a duplicate or incomplete property.");
            }

            if (string.Equals(
                    propertyName,
                    "lockVersion",
                    StringComparison.Ordinal))
            {
                if (reader.TokenType != JsonTokenType.String)
                {
                    throw new JsonException(
                        "The capability ownership lock has no string lockVersion.");
                }

                lockVersion = reader.GetString();
                continue;
            }

            reader.Skip();
        }

        if (!completed ||
            reader.Read() ||
            string.IsNullOrWhiteSpace(lockVersion))
        {
            throw new JsonException(
                "The capability ownership lock is incomplete or has trailing JSON.");
        }

        return lockVersion;
    }
}
