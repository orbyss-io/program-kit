namespace Orbyss.ProgramKit.Workbench.Operations.Extensions;

/// <summary>Exact identity of one explicitly registered in-process Workbench extension.</summary>
/// <param name="Identity">Stable extension identity.</param>
/// <param name="Version">Independent extension API version.</param>
/// <param name="Digest">Digest of the selected implementation.</param>
public sealed record WorkbenchExtensionDescriptor(
    ProgramKitIdentifier Identity,
    SemanticVersion Version,
    Sha256Digest Digest)
{
    /// <summary>Gets the exact extension reference.</summary>
    public ArtifactReference Reference => new(Identity, Version, Digest);
}
