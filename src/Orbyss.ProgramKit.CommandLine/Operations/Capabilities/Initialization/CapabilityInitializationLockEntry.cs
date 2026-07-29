namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

/// <summary>One initialized wrapper and its exact canonical source binding.</summary>
public sealed record CapabilityInitializationLockEntry(
    string CapabilityId,
    string CanonicalSha256,
    string AdapterTemplateSha256,
    string OutputPath,
    string OutputSha256);
