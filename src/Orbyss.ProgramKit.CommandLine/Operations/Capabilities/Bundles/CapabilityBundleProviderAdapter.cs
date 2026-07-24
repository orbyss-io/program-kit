namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Bundles;

/// <summary>One optional provider adapter carried separately from canonical definitions.</summary>
public sealed record CapabilityBundleProviderAdapter(
    string CapabilityId,
    string PackagePath,
    string Provider,
    string Sha256,
    string SourcePath);
