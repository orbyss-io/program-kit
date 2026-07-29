using System.Text.Json;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Payload;

namespace Orbyss.ProgramKit.CommandLine.Operations.Serialization;

/// <summary>Strict source-generated embedded capability catalog reader.</summary>
internal static class ConsumerCapabilityCatalogSerializer
{
    /// <summary>Reads one complete duplicate-free catalog.</summary>
    public static ConsumerCapabilityCatalogDocument Read(
        ReadOnlySpan<byte> content)
    {
        StrictJsonObjectValidator.Validate(content);
        return JsonSerializer.Deserialize(
            content,
            CapabilityInitializationJsonContext.Default
                .ConsumerCapabilityCatalogDocument)
            ?? throw new JsonException(
                "The consumer capability catalog cannot be JSON null.");
    }
}
