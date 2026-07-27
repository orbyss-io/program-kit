using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Clients;

/// <summary>One normalized generated output with exact bytes.</summary>
public sealed record KiotaGeneratedFile(
    string RelativePath,
    long Length,
    Sha256Digest Digest);
