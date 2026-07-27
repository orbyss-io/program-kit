namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

internal sealed record WrapperCandidate(
    string CapabilityId,
    string CanonicalPath,
    string CanonicalSha256,
    string AdapterTemplateSha256,
    string OutputRelativePath,
    string OutputFullPath,
    byte[] OutputBytes,
    string OutputSha256);
