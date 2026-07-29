namespace Orbyss.ProgramKit.CommandLine.Operations.Schemas;

/// <summary>Internal schema candidate before dependency closure is resolved.</summary>
internal sealed record SchemaCatalogCandidate(
    string Id,
    string Version,
    string CanonicalUri,
    string Sha256,
    string OwnerId,
    byte[] Content)
{
    /// <summary>Gets the exact identity and version key.</summary>
    internal string ExactId => string.Concat(Id, "@", Version);
}
