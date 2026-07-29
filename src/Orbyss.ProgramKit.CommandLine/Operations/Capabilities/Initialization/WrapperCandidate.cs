namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

internal sealed record WrapperCandidate(
    string Provider,
    string CapabilityId,
    string CanonicalSha256,
    string AdapterTemplateSha256,
    string OutputRelativePath,
    string OutputFullPath,
    byte[] OutputBytes,
    string OutputSha256);
