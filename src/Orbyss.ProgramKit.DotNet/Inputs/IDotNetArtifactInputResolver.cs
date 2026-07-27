namespace Orbyss.ProgramKit.DotNet.Inputs;

/// <summary>Resolves only exact manifest-listed artifact inputs below a declared read root.</summary>
public interface IDotNetArtifactInputResolver
{
    /// <summary>Reads and verifies the requested exact artifact revision.</summary>
    ValueTask<ResolvedDotNetArtifactInput> ResolveAsync(
        string readRoot,
        DotNetArtifactInputManifest manifest,
        ArtifactReference revision,
        CancellationToken cancellationToken);
}
