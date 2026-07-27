namespace Orbyss.ProgramKit.DotNet.Inputs;

/// <summary>Verified bytes for one exact manifest-listed artifact input.</summary>
public sealed record ResolvedDotNetArtifactInput(
    ArtifactReference Revision,
    string RelativePath,
    ReadOnlyMemory<byte> Content);
