using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>An immutable staged snapshot of versioned nodes and typed dependencies.</summary>
/// <param name="Nodes">All exact revision nodes.</param>
/// <param name="Edges">All typed dependency edges.</param>
public sealed record VersionMapDocument(
    ImmutableArray<VersionRevisionNode> Nodes,
    ImmutableArray<VersionDependencyEdge> Edges);
