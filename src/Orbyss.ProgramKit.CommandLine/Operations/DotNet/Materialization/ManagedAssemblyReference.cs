using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Materialization;

/// <summary>Exact bytes and managed identity for one evaluated reference.</summary>
public sealed record ManagedAssemblyReference(
    string FullPath,
    string Name,
    string AssemblyIdentity,
    Version AssemblyVersion,
    Sha256Digest Digest,
    ReadOnlyMemory<byte> Content,
    bool Consumer);
