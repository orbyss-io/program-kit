using System.Text.Json;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Bundles;

namespace Orbyss.ProgramKit.CommandLine.Operations.Serialization;

/// <summary>Strict source-generated capability bundle manifest reader.</summary>
public sealed class CapabilityBundleManifestReader :
    ICapabilityBundleManifestReader
{
    /// <inheritdoc />
    public CapabilityBundleManifest Read(ReadOnlySpan<byte> content) =>
        JsonSerializer.Deserialize(
            content,
            CapabilityBundleManifestJsonContext.Default.CapabilityBundleManifest)
        ?? throw new JsonException(
            "The capability bundle manifest cannot be JSON null.");
}
