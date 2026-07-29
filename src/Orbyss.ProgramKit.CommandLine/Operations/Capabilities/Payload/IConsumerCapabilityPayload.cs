using System.Collections.Immutable;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Bundles;

namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Payload;

/// <summary>Exact verified read-only capability payload owned by this CLI binary.</summary>
public interface IConsumerCapabilityPayload
{
    /// <summary>Gets the exact embedded bundle manifest.</summary>
    CapabilityBundleManifest Manifest { get; }

    /// <summary>Gets its exact source-byte digest.</summary>
    string ManifestSha256 { get; }

    /// <summary>Gets every release catalog row, including unavailable roles.</summary>
    ImmutableArray<CapabilityKnowledgeClosure> Catalog { get; }

    /// <summary>Gets the exact canonical definition bytes for one consumer capability.</summary>
    ReadOnlyMemory<byte> ReadCapability(string capabilityId);

    /// <summary>Gets the exact reviewed adapter template bytes.</summary>
    ReadOnlyMemory<byte> ReadAdapter(string provider, string capabilityId);

    /// <summary>Gets one exact allow-listed inert supporting resource.</summary>
    ReadOnlyMemory<byte> ReadResource(string resourceId);

    /// <summary>Resolves one release-catalog row.</summary>
    CapabilityKnowledgeClosure ResolveCatalogEntry(string capabilityId);
}
