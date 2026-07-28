namespace Orbyss.ProgramKit.DotNet.Generation.Console.Contracts;

/// <summary>Exact offline proof of verified consumer metadata.</summary>
public sealed record DotNetConsoleMetadataProof(
    Sha256Digest ReferenceAssemblyDigest,
    ImmutableArray<string> VerifiedMetadataNames);
