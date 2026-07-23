namespace Orbyss.ProgramKit.Workbench.Operations.Generation;

/// <summary>Exact evidence for one atomically published output.</summary>
/// <param name="RelativePath">Published relative path.</param>
/// <param name="Digest">Digest of the published bytes.</param>
/// <param name="ByteCount">Published byte count.</param>
public sealed record GeneratedOutputReceipt(
    string RelativePath,
    Sha256Digest Digest,
    long ByteCount);
