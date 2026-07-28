namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Bundles;

/// <summary>One inert exact-byte resource shared by canonical capabilities.</summary>
public sealed record CapabilityBundleSupportingResource(
    string PackagePath,
    string ResourceId,
    string Sha256,
    string SourcePath);
