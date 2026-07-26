using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Clients;

/// <summary>Completed foreign-client generation provenance.</summary>
public sealed record KiotaForeignClientGenerationResult(
    string OutputRoot,
    Sha256Digest InputDigest,
    Sha256Digest LockDigest,
    Sha256Digest GeneratedTreeDigest,
    ImmutableArray<KiotaGeneratedFile> Files,
    ImmutableArray<KiotaRuntimeDependency> RuntimeDependencies);
