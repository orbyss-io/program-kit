using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.CommandLine.Operations.Publishing;

/// <summary>Revalidates a canonical package-root manifest and every selected nupkg.</summary>
public interface ILocalPackageRootVerifier
{
    /// <summary>Returns the verified root or fails closed on any drift or extra package.</summary>
    ValueTask<VerifiedLocalPackageRoot> VerifyAsync(
        string manifestPath,
        ArtifactReference expectedVersionMap,
        ArtifactReference expectedVersionSelection,
        CancellationToken cancellationToken);
}
