using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CommandLine.Operations.Schemas;

/// <summary>One exact package-owned schema and its registered dependencies.</summary>
public sealed record SchemaCatalogEntry(
    string Id,
    string Version,
    string ExactId,
    string CanonicalUri,
    string Sha256,
    string OwnerId,
    ImmutableArray<string> Dependencies,
    ReadOnlyMemory<byte> Content);
