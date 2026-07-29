namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

/// <summary>One wrapper entry from the legacy source-pointer lock.</summary>
public sealed record LegacyCapabilityInitializationLockEntry(
    string CapabilityId,
    string CanonicalPath,
    string CanonicalSha256,
    string AdapterTemplateSha256,
    string OutputPath,
    string OutputSha256);
