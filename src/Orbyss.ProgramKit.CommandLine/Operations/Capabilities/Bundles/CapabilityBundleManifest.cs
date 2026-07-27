namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Bundles;

/// <summary>Exact content allow-list for a Program Kit capability bundle.</summary>
public sealed record CapabilityBundleManifest(
    string BundleVersion,
    CapabilityBundlePayloadEntry[] Capabilities,
    string KitVersion,
    CapabilityBundleProviderAdapter[] OptionalProviderAdapters);
