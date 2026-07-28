namespace Orbyss.ProgramKit.DotNet.Inputs;

/// <summary>Verified bytes for one exact manifest-listed artifact input.</summary>
public sealed record ResolvedDotNetArtifactInput(
    ArtifactReference Revision,
    string RelativePath,
    string FullPath,
    ReadOnlyMemory<byte> Content);
