namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Bundles;

/// <summary>One exact canonical capability payload entry.</summary>
public sealed record CapabilityBundlePayloadEntry(
    string CapabilityId,
    string PackagePath,
    string Sha256,
    string SourcePath);
