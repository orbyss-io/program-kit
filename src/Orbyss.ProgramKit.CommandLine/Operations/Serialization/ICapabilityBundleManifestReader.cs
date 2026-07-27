using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Bundles;

namespace Orbyss.ProgramKit.CommandLine.Operations.Serialization;

/// <summary>Reads one strict source-generated capability bundle manifest.</summary>
public interface ICapabilityBundleManifestReader
{
    /// <summary>Reads exact manifest bytes.</summary>
    CapabilityBundleManifest Read(ReadOnlySpan<byte> content);
}
