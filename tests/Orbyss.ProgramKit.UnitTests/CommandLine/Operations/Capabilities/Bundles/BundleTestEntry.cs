namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.Capabilities.Bundles;

internal sealed record BundleTestEntry(
    string CapabilityId,
    string SourcePath,
    string PackagePath,
    byte[] Content,
    string Digest);
